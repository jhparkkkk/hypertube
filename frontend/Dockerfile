ARG TARGETARCH
FROM --platform=linux/$TARGETARCH node:20

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install --legacy-peer-deps

COPY . .

ARG NODE_ENV=development
ENV NODE_ENV=$NODE_ENV

EXPOSE 3000

ENV CHOKIDAR_USEPOLLING=true

RUN if [ "NODE_ENV" = "production" ]; then npm run build; fi

EXPOSE 3000

CMD [ "sh", "-c", "if [ \"$NODE_ENV\" = \"production\" ]; then npm exec vite preview -- --port 3000; else npm run dev; fi" ]
