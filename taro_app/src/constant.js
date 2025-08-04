let host = window.location.hostname;
if (host.startsWith("taro.")) {
  host = host.replace("taro.", "www.");
  const port = window.location.port ? `:${window.location.port}` : "";
  const newUrl = `${window.location.protocol}//${host}${port}`;
  host = newUrl;
}

export const HOST = host;

export const AI_MODELS = window.__TARO_CONTEXT__?.models.map((model) => {
  return { name: model.name, description: model.description };
});
