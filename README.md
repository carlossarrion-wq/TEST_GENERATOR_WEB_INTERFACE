# Test Plan Generator - Web Interface

Una aplicación web moderna para generar planes de pruebas a partir de requerimientos funcionales utilizando IA.

## 🎯 Características

### 1. Autenticación
- Pantalla de login con diseño moderno
- Validación de credenciales
- Sesión persistente en el navegador

### 2. Configuración del Plan de Pruebas
- **Título del Plan**: Nombre descriptivo para el plan de pruebas
- **Requerimientos Funcionales**: Entrada de texto para especificar los requisitos
- **Porcentaje de Cobertura**: Control deslizante visual (10% - 100%)
  - 10%: Básico
  - 50%: Medio
  - 80%: Alto
  - 100%: Completo
- **Número de Casos de Prueba**: Controles deslizantes para mínimo y máximo

### 3. Generación de Casos de Prueba
Cada caso de prueba generado incluye:
- **Identificador único** (TC-001, TC-002, etc.)
- **Nombre del caso**
- **Descripción detallada**
- **Prioridad** (High, Medium, Low)
- **Precondiciones**
- **Pasos de prueba** (visibles en modal)
- **Resultado esperado**
- **Datos de prueba necesarios**

### 4. Visualización de Resultados
- Tabla HTML responsive con todos los casos de prueba
- Modal flotante para ver los pasos detallados de cada caso
- Diseño limpio y profesional

### 5. Chat de Refinamiento
- Interfaz de chat interactiva con IA
- Permite refinar el plan generado:
  - Añadir casos específicos
  - Incluir escenarios negativos
  - Agregar pruebas de seguridad/rendimiento
  - Modificar casos existentes
  - Eliminar casos redundantes

### 6. Opciones de Exportación
- **CSV**: Formato tabular para Excel/Sheets
- **JSON**: Formato estructurado para integración
- **BDD (Gherkin)**: Formato .feature para Cucumber/SpecFlow

### 7. Gestión de Planes
- **Guardar**: Almacena el plan en localStorage para recuperarlo después
- **Nuevo Plan**: Comienza un plan desde cero
- **Descartar**: Elimina el plan actual (con confirmación)

## 🎨 Diseño

El diseño está basado en el dashboard de referencia AWS Bedrock Usage Control, utilizando:
- **Fuente**: Amazon Ember
- **Colores principales**: 
  - Teal/Verde azulado (#319795, #2c7a7b)
  - Grises (#4a5568, #2d3748)
- **Efectos**: Glassmorphism, gradientes, sombras suaves
- **Animaciones**: Transiciones suaves y efectos hover

## 📁 Estructura del Proyecto

```
TEST_GENERATOR_WEB_INTERFACE/
├── login.html              # Página de autenticación
├── index.html              # Dashboard principal
├── css/
│   └── styles.css         # Estilos completos de la aplicación
├── js/
│   └── app.js             # Lógica de la aplicación
└── README.md              # Este archivo
```

## 🚀 Uso

### 1. Iniciar la Aplicación
Abre `login.html` en tu navegador web.

### 2. Autenticación
- Introduce cualquier usuario y contraseña (mockup)
- Haz clic en "Sign In"

### 3. Crear un Plan de Pruebas
1. Introduce un título para el plan
2. Escribe los requerimientos funcionales (uno por línea)
3. Ajusta el porcentaje de cobertura deseado
4. Establece el número mínimo y máximo de casos
5. Haz clic en "Generate Test Plan"

### 4. Revisar y Refinar
- Revisa los casos generados en la tabla
- Haz clic en "View Steps" para ver los pasos detallados
- Usa el chat para refinar el plan con IA
- Solicita cambios específicos al asistente

### 5. Exportar o Guardar
- **Guardar**: Para continuar trabajando después
- **Exportar CSV**: Para usar en Excel
- **Exportar JSON**: Para integración con sistemas
- **Exportar BDD**: Para frameworks de testing

## 🔧 Características Técnicas

### Frontend
- HTML5 semántico
- CSS3 con variables personalizadas
- JavaScript vanilla (ES6+)
- Diseño responsive (mobile-first)
- Accesibilidad (ARIA labels, keyboard navigation)

### Almacenamiento
- SessionStorage: Autenticación
- LocalStorage: Planes guardados

### Controles Personalizados
- Sliders con gradientes de color
- Valores dinámicos que se actualizan en tiempo real
- Validación de rangos (min ≤ max)

### Animaciones
- Fade in/out para modales
- Slide up para mensajes de chat
- Transiciones suaves en hover
- Loading spinners durante procesamiento

## 🎯 Próximos Pasos (Integración Real)

Para convertir este mockup en una aplicación funcional:

1. **Backend Lambda Function**
   - Crear función Lambda en AWS
   - Integrar con Amazon Bedrock para generación IA
   - Implementar lógica de generación de casos de prueba

2. **API Gateway**
   - Configurar endpoints REST
   - Implementar autenticación (Cognito)
   - Gestionar CORS

3. **Base de Datos**
   - DynamoDB para almacenar planes
   - S3 para archivos exportados
   - CloudWatch para logs

4. **Mejoras de UI**
   - Indicadores de progreso más detallados
   - Historial de planes generados
   - Comparación entre versiones
   - Colaboración en tiempo real

## 📝 Notas de Implementación

### Controles Deslizantes
Los sliders utilizan un gradiente de colores que representa visualmente los niveles:
- Amarillo (10%): Cobertura básica
- Verde claro (50%): Cobertura media
- Verde (80%): Cobertura alta
- Teal (100%): Cobertura completa

### Modal de Pasos
El modal muestra información detallada de cada caso:
- Descripción completa
- Precondiciones necesarias
- Datos de prueba requeridos
- Pasos numerados y secuenciales
- Resultado esperado

### Chat IA (Simulado)
El chat actualmente simula respuestas basadas en palabras clave:
- "add/include" → Sugerencias para añadir casos
- "remove/delete" → Ayuda para eliminar redundancias
- "modify/change" → Asistencia para modificar casos
- "security/performance" → Casos especializados

## 🎨 Personalización

Para adaptar el diseño a tu marca:

1. **Colores**: Modifica las variables CSS en `styles.css`
2. **Fuente**: Cambia la fuente en el `<head>` de los HTML
3. **Logo**: Añade tu logo en el header
4. **Textos**: Personaliza los mensajes y etiquetas

## 📄 Licencia

Este es un proyecto de demostración/mockup para visualizar el diseño y flujo de la aplicación.

## 👤 Autor

Desarrollado como mockup de interfaz para el generador de planes de pruebas con IA.

---

**Nota**: Esta es una versión mockup/demo. La generación real de casos de prueba requiere integración con servicios de IA (AWS Bedrock Lambda).
