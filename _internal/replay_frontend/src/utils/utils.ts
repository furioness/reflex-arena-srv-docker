export function formatDate(date: Date): string {
  let formatter
  if (date.getFullYear() == new Date().getFullYear()) {
    formatter = new Intl.DateTimeFormat(undefined, {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })
  } else {
    formatter = new Intl.DateTimeFormat(undefined, {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }
  return formatter.format(date)
}

export function getReplayUrl(filename: string): string {
  return `/replays/${filename}`
}
