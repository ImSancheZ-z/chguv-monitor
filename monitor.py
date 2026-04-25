#!/usr/bin/env python3
"""
Monitor de convocatorias CHGUV - Bolsa de Empleo Temporal
Detecta nuevas entradas marcadas como NUEVO y avisa por Telegram.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://chguv.san.gva.es/rrhh/seleccion/bolsa-de-trabajo/convocatorias-bolsa-de-empleo-temporal"
SNAPSHOT_FILE = Path("data/snapshot.json")
TELEGRAM_CHAT_ID = "911700880"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CHGUV-Monitor/1.0)"
}


def fetch_page() -> BeautifulSoup:
    """Descarga y parsea la página web."""
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_nuevo_items(soup: BeautifulSoup) -> list[dict]:
    """
    Extrae todos los elementos marcados como NUEVO en la página.
    Devuelve una lista de dicts con 'context'.
    """
    items = []
    seen = set()

    for tag in soup.find_all(["strong", "b"]):
        text = tag.get_text(strip=True)
        if "NUEVO" not in text.upper():
            continue

        parent = tag.parent
        context = ""

        for ancestor in [parent] + list(parent.parents)[:3]:
            ancestor_text = ancestor.get_text(separator=" ", strip=True)
            ancestor_text = re.sub(r'\s+', ' ', ancestor_text).strip()
            if len(ancestor_text) > 20:
                context = ancestor_text[:400]
                break

        key = context[:100] if context else text
        if key not in seen:
            seen.add(key)
            items.append({
                "context": context,
                "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

    return items


def load_snapshot() -> dict:
    """Carga el snapshot guardado anteriormente."""
    if SNAPSHOT_FILE.exists():
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": [], "last_check": None}


def save_snapshot(data: dict) -> None:
    """Guarda el snapshot actualizado."""
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_new_items(current: list[dict], previous: list[dict]) -> list[dict]:
    """Devuelve los items que son genuinamente nuevos."""
    previous_keys = {item["context"][:100] for item in previous}
    return [item for item in current if item["context"][:100] not in previous_keys]


def send_telegram(message: str) -> None:
    """Envía un mensaje por Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("⚠️  TELEGRAM_BOT_TOKEN no definido.")
        return

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(api_url, json=payload, timeout=15)
    if response.status_code == 200:
        print("✅ Mensaje Telegram enviado correctamente")
    else:
        print(f"❌ Error Telegram: {response.status_code} - {response.text}")


def build_alert_message(new_items: list[dict]) -> str:
    """Construye el mensaje de alerta cuando hay novedades."""
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = [
        "🚨 <b>NUEVAS CONVOCATORIAS CHGUV</b>",
        f"📅 {today}",
        "",
        f"Se han detectado <b>{len(new_items)} entrada(s) nueva(s)</b>:",
        "",
    ]

    for i, item in enumerate(new_items, 1):
        context = item["context"]
        context = re.sub(r'^NUEVO\s*', '', context, flags=re.IGNORECASE).strip()
        if len(context) > 300:
            context = context[:297] + "..."
        lines.append(f"<b>{i}.</b> {context}")
        lines.append("")

    lines.append(f'🔗 <a href="{URL}">Ver página completa</a>')
    return "\n".join(lines)


def build_ok_message(total_items: int, last_check: str | None) -> str:
    """Construye el mensaje cuando no hay novedades."""
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    last = f"Última comprobación anterior: {last_check}" if last_check else "Primera ejecución"
    return (
        f"✅ <b>CHGUV Bolsa de Empleo</b>\n"
        f"📅 {today}\n"
        f"\n"
        f"Sin cambios desde la última comprobación.\n"
        f"Items 'NUEVO' en la web ahora: <b>{total_items}</b>\n"
        f"{last}\n"
        f"\n"
        f'🔗 <a href="{URL}">Ver página</a>'
    )


def main():
    print(f"🔍 Comprobando: {URL}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. Descargar página
    try:
        soup = fetch_page()
        print("✅ Página descargada")
    except Exception as e:
        msg = f"❌ <b>CHGUV Monitor - Error</b>\n\nNo se pudo descargar la página:\n<code>{e}</code>"
        send_telegram(msg)
        sys.exit(1)

    # 2. Extraer items NUEVO actuales
    current_items = extract_nuevo_items(soup)
    print(f"📋 Items 'NUEVO' en la página: {len(current_items)}")

    # 3. Cargar snapshot anterior
    snapshot = load_snapshot()
    previous_items = snapshot.get("items", [])
    print(f"💾 Items en snapshot anterior: {len(previous_items)}")

    # 4. Detectar novedades
    new_items = find_new_items(current_items, previous_items)
    print(f"🆕 Items nuevos: {len(new_items)}")

    # 5. Enviar mensaje Telegram
    if new_items:
        print("\n🚨 ¡Nuevas convocatorias detectadas!")
        for item in new_items:
            print(f"   → {item['context'][:100]}")
        send_telegram(build_alert_message(new_items))
    else:
        print("\n✅ Sin cambios.")
        send_telegram(build_ok_message(len(current_items), snapshot.get("last_check")))

    # 6. Guardar snapshot actualizado
    save_snapshot({
        "items": current_items,
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "url": URL,
    })
    print(f"💾 Snapshot guardado en {SNAPSHOT_FILE}")


if __name__ == "__main__":
    main()
