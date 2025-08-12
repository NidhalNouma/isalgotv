let host: string = window.location.hostname;
if (host.startsWith("tero.")) {
  host = host.replace("tero.", "www.");
  const port: string = window.location.port ? `:${window.location.port}` : "";
  const newUrl: string = `${window.location.protocol}//${host}${port}`;
  host = newUrl;
}

export const HOST: string = host;

export interface AIModel {
  name: string;
  description: string;
}

// Tell TypeScript about the shape of window.__TERO_CONTEXT__
declare global {
  interface Window {
    __TERO_CONTEXT__?: {
      models: AIModel[];
    };
  }
}

export const AI_MODELS: AIModel[] | undefined = window.__TERO_CONTEXT__?.models?.map((model: { name: string; description: string }) => {
  return { name: model.name, description: model.description };
});

function getCookie(name: string): string | null {
  const cookies = document.cookie.split(";").map((c) => c.trim());
  for (const c of cookies) {
    if (c.startsWith(name + "=")) {
      return decodeURIComponent(c.substring(name.length + 1));
    }
  }
  return null;
}

export const csrf_token: string | null = getCookie("csrftoken");