/* HD Hope CMS — Supabase 連線設定
 *
 * 1) 到 Supabase 建立專案，Project Settings → API 取得：
 *      Project URL        → 貼到 SUPABASE_URL
 *      anon public key    → 貼到 SUPABASE_ANON_KEY
 *    anon key 是公開金鑰，放在前端沒有問題；真正的權限由資料庫 RLS 控制。
 *
 * 2) 在 SQL Editor 執行 supabase/schema.sql，並在 Authentication → Users 建立管理員帳號，
 *    再執行 schema.sql 最下方的 insert 讓該帳號進入 admins 白名單。
 *
 * 3) （選用）PUBLISH_WEBHOOK：把官網重新產生流程接起來。
 *    留空時，GitHub Actions 會每 15 分鐘自動重建一次官網；
 *    填入 webhook 後，按下「發布」會立即觸發重建。
 */
window.HD_CONFIG = {
  SUPABASE_URL: "https://usuzdpavetppruewiffs.supabase.co
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVzdXpkcGF2ZXRwcHJ1ZXdpZmZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQzMDYwMTQsImV4cCI6MjEwOTg4MjAxNH0.GHR2uIlgJezCHkG1heYmxSz3QW40F9Z69Ivtsq6yjo4",
  PUBLISH_WEBHOOK: "",
  SITE_BASE: "https://hdhopehair.com"
};
