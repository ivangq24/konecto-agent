# Dockerfile optimizado para DESARROLLO

FROM node:18-alpine

# Establecer variables de entorno para desarrollo
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1
ENV WATCHPACK_POLLING=true

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para desarrollo
RUN apk add --no-cache \
    libc6-compat \
    git \
    vim \
    curl \
    htop \
    procps

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar TODAS las dependencias (incluyendo devDependencies)
RUN npm install

# Crear directorio para logs de desarrollo
RUN mkdir -p /app/logs

# Exponer puerto
EXPOSE 3000

# Comando para ejecutar la aplicación en modo desarrollo con hot-reload
CMD ["npm", "run", "dev"]
