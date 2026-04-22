export const appConfig = {
  name: process.env.NEXT_PUBLIC_APP_NAME ?? "RebaTox",
  apiBaseUrl: (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
    /\/$/,
    "",
  ),
};
