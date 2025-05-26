# Debugging Guide for Duelo de Plumas

This guide explains how to debug both the frontend and backend of the Duelo de Plumas application.

## Backend Debugging (Already Configured)

The backend is already set up for debugging with `debugpy`. 

1. Start the application with `docker-compose up`
2. In VS Code/Cursor, go to the Debug panel (Ctrl+Shift+D)
3. Select "Python: Attach to Docker (FastAPI)" from the dropdown
4. Click the play button to attach the debugger
5. Set breakpoints in your Python code
6. The debugger will stop at breakpoints when the code is executed

## Frontend Debugging (New Setup)

I've set up three different ways to debug your React + Vite frontend:

### Option 1: Browser Debugging (Recommended)

This allows you to debug your React components and TypeScript code directly in the browser.

1. Start your application with `docker-compose up`
2. In VS Code/Cursor, go to the Debug panel (Ctrl+Shift+D)
3. Select "Frontend: Launch Chrome Debug" from the dropdown
4. Click the play button - this will launch Chrome with debugging enabled
5. Set breakpoints in your React components (`.tsx` files)
6. Navigate to your app and the debugger will stop at breakpoints

### Option 2: Attach to Running Chrome

If you prefer to use your existing Chrome instance:

1. First, start Chrome with remote debugging:
   - Run the task "Start Chrome with Remote Debugging" (Ctrl+Shift+P → "Tasks: Run Task")
   - OR manually start Chrome with: `chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug`
2. Navigate to `http://localhost:3001` in that Chrome instance
3. In VS Code/Cursor, select "Frontend: Attach to Chrome" from the debug dropdown
4. Click the play button to attach
5. Set breakpoints and debug as usual

### Option 3: Debug the Vite Dev Server

This debugs the Node.js side (the Vite development server itself):

1. Stop the Docker frontend service
2. In VS Code/Cursor, select "Frontend: Debug Vite Dev Server"
3. Click the play button - this will start Vite outside of Docker
4. You can debug Vite configuration issues, plugins, etc.

## Setting Breakpoints

### React/TypeScript Code
- Open any `.tsx` or `.ts` file in your frontend
- Click in the left margin next to a line number to set a breakpoint
- The red dot indicates an active breakpoint
- When the code executes, the debugger will pause at that line

### Debugging Tips

1. **Source Maps**: I've enabled source maps in your Vite config, so you'll see your original TypeScript code, not transpiled JavaScript

2. **Skip Files**: The debug configurations are set to skip `node_modules` and internal files, focusing on your code

3. **Smart Stepping**: Enabled smart stepping to avoid stepping through generated code

4. **Variables and Call Stack**: When paused at a breakpoint, you can:
   - Inspect variables in the Variables panel
   - See the call stack in the Call Stack panel
   - Use the Debug Console to evaluate expressions

## Docker Debugging Options

If you want to debug the Vite dev server while running in Docker:

1. In `docker-compose.yml`, uncomment the debug command for the frontend service
2. Uncomment the port mapping for `9229:9229`
3. Run `docker-compose up --build`
4. The Vite server will run with Node.js debugging enabled

## Troubleshooting

### Chrome Won't Connect
- Make sure port 9222 isn't already in use
- Try closing all Chrome instances and restarting
- Check if Chrome is installed and accessible from command line

### Source Maps Not Working
- Make sure `sourcemap: true` is in your `vite.config.ts` (already added)
- Clear browser cache and restart the dev server

### Breakpoints Not Hitting
- Make sure the file path matches exactly
- Try refreshing the page after setting breakpoints
- Check that the source maps are loading correctly in browser dev tools

## Useful Keyboard Shortcuts

- **F5**: Start debugging
- **F9**: Toggle breakpoint
- **F10**: Step over
- **F11**: Step into
- **Shift+F11**: Step out
- **Ctrl+Shift+F5**: Restart debugging
- **Shift+F5**: Stop debugging

## Comparison with Backend Debugging

| Feature | Backend (Python) | Frontend (React/TS) |
|---------|------------------|---------------------|
| Debugger | debugpy | Chrome DevTools |
| Port | 5678 | 9222 (attach mode) |
| Breakpoints | ✅ Python files | ✅ TypeScript/React files |
| Variable inspection | ✅ | ✅ |
| Call stack | ✅ | ✅ |
| Hot reload | ✅ (uvicorn --reload) | ✅ (Vite HMR) |

Both debugging setups now provide the same level of debugging capabilities! 