/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  readonly VITE_API_TIMEOUT_MS?: string;
  readonly VITE_LOG_RAW_BODIES?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
