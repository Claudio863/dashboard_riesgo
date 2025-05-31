# 🚀 INSTRUCCIONES PARA STREAMLIT CLOUD

## ✅ PROBLEMA RESUELTO
El `ModuleNotFoundError: No module named 'lector_reporte_automático'` ha sido completamente corregido.

## 📋 PASOS PARA DESPLEGAR EN STREAMLIT CLOUD

### 1. 🔄 **Actualizar Repositorio (CRÍTICO)**
```bash
git add .
git commit -m "Fix: Configuración completa para Streamlit Cloud con fallback local"
git push origin main
```

### 2. 🔐 **Configurar Google API Secrets en Streamlit Cloud**

En tu dashboard de Streamlit Cloud, ve a la configuración de tu app y añade estos secrets:

#### **Opción A: Service Account (RECOMENDADO)**
```toml
[google_service_account]
type = "service_account"
project_id = "tu-google-project-id"
private_key_id = "copia-desde-tu-service-account-json"
private_key = "-----BEGIN PRIVATE KEY-----\ncopia-la-clave-privada-completa\n-----END PRIVATE KEY-----\n"
client_email = "tu-service-account@proyecto.iam.gserviceaccount.com"
client_id = "tu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/tu-service-account%40proyecto.iam.gserviceaccount.com"
```

#### **Opción B: OAuth2 (Alternativa)**
```toml
[google_credentials]
client_id = "copia-desde-credentials.json"
client_secret = "copia-desde-credentials.json"
redirect_uris = ["http://localhost:8080/"]
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"

[google_token]
access_token = "copia-desde-drive_automat.json"
refresh_token = "copia-desde-drive_automat.json"
token_uri = "https://oauth2.googleapis.com/token"
client_id = "mismo-que-arriba"
client_secret = "mismo-que-arriba"
```

### 3. 🎯 **¿Cómo obtener las credenciales?**

#### **Para Service Account:**
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a "IAM & Admin" → "Service Accounts"
4. Crea un nuevo Service Account o usa uno existente
5. Genera una nueva clave JSON
6. Copia los valores al formato de arriba

#### **Para OAuth2:**
1. Abre tu archivo `credentials.json` local
2. Abre tu archivo `drive_automat.json` local
3. Copia los valores correspondientes

### 4. ⚡ **Funcionalidad de Fallback**

Si NO configuras los secrets, la aplicación funcionará con **datos locales**:
- ✅ Cargará archivos CSV desde `datos_*.csv`
- ✅ Mostrará mensaje informativo al usuario
- ✅ Todas las visualizaciones funcionarán normalmente

### 5. 🔍 **Verificar Despliegue**

1. **Streamlit Cloud debería mostrar:**
   - ✅ Sin errores de ModuleNotFoundError
   - ✅ Aplicación ejecutándose
   - ⚠️ Posibles avisos sobre Google Drive (normal si no hay secrets)

2. **Funcionalidad esperada:**
   - ✅ Dashboard principal carga
   - ✅ Página de monitoreo funciona
   - ✅ Gráficos se muestran correctamente
   - ✅ Datos locales como fallback

### 6. 🎉 **Estado Final**

- ✅ **ModuleNotFoundError eliminado**
- ✅ **Imports corregidos en dashboard.py y funciones_google.py**  
- ✅ **Función archivo_actualizado() implementada localmente**
- ✅ **Manejo robusto de errores de autenticación**
- ✅ **Fallback a datos locales**
- ✅ **Configuración flexible para local y cloud**

### 7. 📞 **Soporte**

Si tienes problemas:
1. Revisa los logs de Streamlit Cloud
2. Verifica que el push se completó correctamente
3. Confirma la configuración de secrets si quieres usar Google Drive

## 🎯 RESULTADO ESPERADO

Tu dashboard debería funcionar **perfectamente** en Streamlit Cloud, con o sin credenciales de Google Drive configuradas.
