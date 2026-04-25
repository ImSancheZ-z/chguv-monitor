# 🏥 Monitor - CHGUV Bolsa de Empleo Temporal

Monitor automático que detecta nuevas convocatorias en la bolsa de empleo del Hospital General Universitario de Valencia y avisa por **Telegram**.

**Página monitoreada:**  
👉 https://chguv.san.gva.es/rrhh/seleccion/bolsa-de-trabajo/convocatorias-bolsa-de-empleo-temporal

---

## ¿Cómo funciona?

1. Cada día GitHub Actions ejecuta el script automáticamente.
2. Descarga la página y busca todos los elementos marcados como **"NUEVO"**.
3. Compara con el snapshot guardado del día anterior.
4. **Siempre te manda un mensaje por Telegram:**
   - 🚨 Si hay novedades → te muestra qué ha cambiado
   - ✅ Si no hay nada nuevo → te confirma que todo sigue igual
5. Guarda el snapshot actualizado en el repo.

---

## ⚙️ Configuración (una sola vez)

### 1. Sube el proyecto a GitHub

```bash
git init
git add .
git commit -m "feat: monitor CHGUV"
git remote add origin https://github.com/TU_USUARIO/chguv-monitor.git
git push -u origin main
```

### 2. Añade el token de Telegram como Secret

En tu repositorio de GitHub:
- Ve a **Settings → Secrets and variables → Actions**
- Pulsa **"New repository secret"**
- Nombre: `TELEGRAM_BOT_TOKEN`
- Valor: el token de tu bot (el que te dio @BotFather, formato: `123456:ABC-DEF...`)
- Guarda

### 3. Activa permisos de escritura del workflow

- Ve a **Settings → Actions → General**
- En "Workflow permissions" selecciona **"Read and write permissions"**
- Guarda

---

## ▶️ Probar que funciona

Lanza el workflow manualmente desde:  
**GitHub → Actions → Monitor CHGUV → Run workflow**

Deberías recibir un mensaje en Telegram en segundos.

---

## ⏰ Cambiar la frecuencia

Edita `.github/workflows/monitor.yml`, línea `cron`:

| Frecuencia | Cron |
|---|---|
| Cada día a las 8h | `0 6 * * *` |
| Cada 2 días a las 8h | `0 6 */2 * *` |
| Lunes y jueves | `0 6 * * 1,4` |

---

## 📁 Estructura

```
chguv-monitor/
├── .github/
│   └── workflows/
│       └── monitor.yml     ← GitHub Actions (schedule + permisos)
├── data/
│   └── snapshot.json       ← Estado actual (se actualiza automáticamente)
├── monitor.py              ← Script principal
└── README.md
```

---

## 🧪 Probar en local

```bash
pip install requests beautifulsoup4
export TELEGRAM_BOT_TOKEN="tu_token_aqui"
python monitor.py
```
