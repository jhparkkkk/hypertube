ARG TARGETARCH
FROM --platform=linux/$TARGETARCH node:20

WORKDIR /app

COPY package.json package-lock.json ./

# Exécuter npm install dans Docker (et non sur Mac)
RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
