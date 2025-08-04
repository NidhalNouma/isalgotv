let host = window.location.hostname;
if (host.startsWith("tero.")) {
  host = host.replace("tero.", "www.");
  const port = window.location.port ? `:${window.location.port}` : "";
  const newUrl = `${window.location.protocol}//${host}${port}`;
  host = newUrl;
}

export const HOST = host;

export const AI_MODELS = window.__TERO_CONTEXT__?.models.map((model) => {
  return { name: model.name, description: model.description };
});
