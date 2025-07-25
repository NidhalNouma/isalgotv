let host = window.location.hostname;
if (host.startsWith("saro.")) {
  host = host.replace("saro.", "www.");
  const port = window.location.port ? `:${window.location.port}` : "";
  const newUrl = `${window.location.protocol}//${host}${port}`;
  host = newUrl;
}

export const HOST = host;

export const AI_MODELS = [
  { name: "TR-A5", description: "Best for common use" },
  { name: "TR-H6 ", description: "Best for reasoning" },
];
