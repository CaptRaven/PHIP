FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* /app/
RUN npm install
COPY index.html /app/index.html
COPY vite.config.js /app/vite.config.js
COPY postcss.config.js /app/postcss.config.js
COPY tailwind.config.js /app/tailwind.config.js
COPY src /app/src
COPY public /app/public
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
