# Git - Guía Rápida para RE Expert

## Antes de empezar a trabajar (Pull / Retrieve)

```bash
cd "C:\Users\matia\OneDrive\Escritorio\mio\Proyectos\ChatBotAi Real State"
git pull origin main
```

Si tenés cambios locales sin commitear y te da conflicto:
```bash
git stash
git pull origin main
git stash pop
```

---

## Cuando terminás de trabajar (Commit + Push)

### 1. Ver qué cambió
```bash
git status
```

### 2. Agregar archivos al commit
```bash
# Agregar un archivo específico:
git add index.html

# Agregar todos los cambios:
git add .
```

### 3. Hacer el commit
```bash
git commit -m "Descripción breve de lo que hiciste"
```

### 4. Subir a GitHub
```bash
git push origin main
```

---

## Comando completo (copy-paste rápido)

**Pull:**
```bash
cd "C:\Users\matia\OneDrive\Escritorio\mio\Proyectos\ChatBotAi Real State" && git pull origin main
```

**Commit + Push:**
```bash
cd "C:\Users\matia\OneDrive\Escritorio\mio\Proyectos\ChatBotAi Real State" && git add . && git commit -m "tu mensaje" && git push origin main
```

---

## Tips
- Siempre hacé `git pull` antes de empezar para tener la última versión
- Siempre hacé `git push` cuando terminás para no perder trabajo
- Si algo sale mal: `git log --oneline -5` para ver los últimos commits
