# Centro de Monitoreo de Red (NMS Ligero)

## 🚀 Requisitos previos

- Docker y Docker Compose (recomendado)
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

## 📥 Instalación Rápida

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Clonar el repositorio
git clone <tu-repo>
cd monitoreo-app

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Levantar el proyecto
docker-compose up -d --build

# 4. Acceder a http://localhost:8000