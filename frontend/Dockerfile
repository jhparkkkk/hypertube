ARG TARGETARCH
FROM --platform=linux/$TARGETARCH node:20

ARG VITE_CLIENT_ID
ARG VITE_CLIENT_SECRET

ENV VITE_CLIENT_ID=$VITE_CLIENT_ID
ENV VITE_CLIENT_SECRET=$VITE_CLIENT_SECRET

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install --legacy-peer-deps

COPY . .

ARG NODE_ENV=production
ENV NODE_ENV=$NODE_ENV



ENV CHOKIDAR_USEPOLLING=true

RUN echo "🌿 Running build in $NODE_ENV" && npm run build

EXPOSE 3000

CMD [ "sh", "-c", "npm exec vite preview -- --port 3000 --host" ]
