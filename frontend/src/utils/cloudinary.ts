export function cdnUrl(url: string, width: number): string {
  if (!url) return url
  return url.replace('/upload/', `/upload/w_${width},c_limit,f_auto,q_auto/`, 1)
}
