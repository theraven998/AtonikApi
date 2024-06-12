# Documentación de la API

## Descripción General
Esta API permite la gestión de usuarios, incluyendo el registro, inicio de sesión y la obtención de información del usuario. La API utiliza JWT para la autenticación y MongoDB para el almacenamiento de datos.

## Rutas de la API

### 1. Registro de Usuario

- **Ruta**: `/api/register`
- **Método**: `POST`
- **Descripción**: Registra un nuevo usuario en la base de datos.
- **Datos del Request**:
  ```json
  {
    "name": "Nombre del usuario",
    "password": "Contraseña del usuario",
    "phone": "Teléfono del usuario",
    "birthdate": "Fecha de nacimiento del usuario (YYYY-MM-DD)",
    "document_number": "Número de documento del usuario"
  }

