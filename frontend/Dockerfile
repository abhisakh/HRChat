FROM node:20

WORKDIR /app

# Ensure dev dependencies (vite) are installed
ENV NODE_ENV=development

# Copy only dependency files first (better caching)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of the source code
COPY . .

# Expose Vite dev server
EXPOSE 5173

# Run dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]