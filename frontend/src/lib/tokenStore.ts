const TOKEN_KEY = "experiment-token";

// sessionStorage: a refresh keeps your seat, while each new tab / window is a
// new participant (handy for demoing three players on one machine).
export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};
