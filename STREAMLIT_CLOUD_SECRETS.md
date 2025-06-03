# Configuración de Secretos para Streamlit Cloud

Este documento explica cómo configurar los secretos necesarios para que la aplicación funcione correctamente en Streamlit Cloud.

## Requisitos Previos

1. **Cuenta de servicio de Google**: Necesitas una cuenta de servicio (service account) con acceso a Google Drive
2. **Archivo de credenciales JSON**: Debes tener el archivo de credenciales de la cuenta de servicio

## Pasos para Configurar los Secretos

### 1. Acceder a la Configuración de Secretos

1. Ve a tu aplicación en [Streamlit Cloud](https://share.streamlit.io/)
2. Haz clic en el botón "⚙️ Settings" en la esquina superior derecha
3. Selecciona la pestaña "Secrets"

### 2. Configurar los Secretos de Google Drive

En el editor de secretos, agrega la siguiente configuración TOML:

```toml
[google_drive]
project_id = "tu-project-id"
private_key_id = "tu-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\ntu-private-key-aqui\n-----END PRIVATE KEY-----\n"
client_email = "tu-service-account@tu-project.iam.gserviceaccount.com"
client_id = "tu-client-id"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/tu-service-account%40tu-project.iam.gserviceaccount.com"
```

### 3. Obtener los Valores de tu Archivo JSON

Abre tu archivo de credenciales JSON (por ejemplo, `drive_automat.json`) y copia los valores correspondientes:

- `project_id`: Valor del campo `"project_id"`
- `private_key_id`: Valor del campo `"private_key_id"`
- `private_key`: Valor del campo `"private_key"` (¡IMPORTANTE! Mantén los `\n` tal como aparecen)
- `client_email`: Valor del campo `"client_email"`
- `client_id`: Valor del campo `"client_id"`
- `client_x509_cert_url`: Valor del campo `"client_x509_cert_url"`

### 4. Notas Importantes

#### Formateo de la Clave Privada
- La clave privada debe mantenerse con los caracteres `\n` para las nuevas líneas
- NO reemplaces los `\n` con saltos de línea reales en el editor de secretos
- Ejemplo correcto: `"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n"`

#### Seguridad
- ❌ **NUNCA** subas estos secretos a GitHub
- ❌ **NUNCA** compartas estos valores en público
- ✅ **SOLO** agrégalos en la configuración de secretos de Streamlit Cloud

### 5. Verificación

Una vez configurados los secretos:

1. Guarda la configuración
2. Reinicia tu aplicación en Streamlit Cloud
3. La aplicación debería conectarse automáticamente a Google Drive usando los secretos

### 6. Troubleshooting

#### Error: "No se pudo conectar a Google Drive"
- Verifica que todos los campos estén correctamente copiados
- Asegúrate de que la clave privada mantenga el formato con `\n`
- Verifica que la cuenta de servicio tenga permisos de acceso a las carpetas de Google Drive

#### Error: "google_drive not in st.secrets"
- Confirma que la sección `[google_drive]` esté correctamente definida
- Verifica que no haya errores de sintaxis TOML

## Ejemplo de Configuración Completa

```toml
[google_drive]
project_id = "mi-proyecto-123456"
private_key_id = "abc123def456ghi789"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n"
client_email = "dashboard-service@mi-proyecto-123456.iam.gserviceaccount.com"
client_id = "123456789012345678901"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/dashboard-service%40mi-proyecto-123456.iam.gserviceaccount.com"
```

## Soporte

Si tienes problemas con la configuración, revisa:
1. Los logs de la aplicación en Streamlit Cloud
2. Que la cuenta de servicio tenga los permisos correctos
3. Que los IDs de las carpetas de Google Drive sean correctos
