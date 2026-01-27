<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import MatchList from '@/components/MatchList.vue'
import type {ChunkHeader, DBHeader, Matches} from '@/types/db-json'

const DB_ROOT = '/db'
const REPLAYS_ROOT = '/replays'

async function loadDBHeader() {
  const HEADER_URL = `${DB_ROOT}/replays_header.json`

  const response = await fetch(HEADER_URL)
  if (!response.ok) {
    throw new Error(`Failed fetching Replay Header DB, status: ${response.status}`)
  }

  const result: DBHeader = await response.json()
  result.updated_at = new Date(result.updated_at)
  for (const chunk of result.chunk_headers) {
    chunk.oldest_replay_ts = new Date(chunk.oldest_replay_ts)
    chunk.latest_replay_ts = new Date(chunk.latest_replay_ts)
  }
  return result as DBHeader
}

async function loadChunk(chunk: ChunkHeader) {
  const response = await fetch(`${DB_ROOT}/${chunk.filename}`)
  if (!response.ok) {
    throw new Error(`Failed fetching Replay Header DB, status: ${response.status}`)
  }

  const result = (await response.json()) as Matches
  for (const match of Object.values(result)) {
    match.finished_at = new Date(match.finished_at)
    if (match.metadata) {
      match.metadata.started_at = new Date(match.metadata.started_at)
    }
  }
  return result
}

const matches = ref<Matches>({})
const header = ref<DBHeader | null>(null)

onMounted(async () => {
  header.value = await loadDBHeader()

  // reversing, so we can start with the latest matches
  // which will render immediately, as the final list is reactive
  for (const chunkHeader of header.value.chunk_headers.slice().reverse()) {
    const matchesChunk = await loadChunk(chunkHeader)

    Object.assign(matches.value, matchesChunk)
  }
  console.debug(`Loaded ${Object.keys(matches.value).length} matches`)
})
</script>

<template>
  <header>
    <h1>Reflex Arena matches</h1>
    <a :href="REPLAYS_ROOT + '/'">Raw list</a>
  </header>

  <MatchList :matches="matches"/>
</template>

<style scoped>
header {
  display: flex;
  align-items: baseline; /* aligns text nicely */
  gap: 1rem;
}
</style>
