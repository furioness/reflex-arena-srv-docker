<script lang="ts" setup>
import MatchDigest from '@/components/MatchDigest.vue'
import {computed, type ComputedRef} from 'vue'
import type {Match, Matches} from '@/types/db-json'

const props = defineProps<{ matches: Matches }>()

const orderedMatches: ComputedRef<Array<[string, Match]>> = computed(() => {
  return Object.entries(props.matches).sort(
    ([, a], [, b]) => b.finished_at.getTime() - a.finished_at.getTime(),
  )
})
</script>

<template>
  <!--  header-->
  <div class="match-row">
    <div class="cell date">Date</div>
    <div class="cell mode">Mode</div>
    <div class="cell download">Download</div>
    <div class="cell marker-count">Marker<br/>count</div>
    <div class="cell map">Map</div>
    <div class="cell players">Players</div>
  </div>
  <MatchDigest
    v-for="[filename, match] in orderedMatches"
    :key="filename"
    :filename="filename"
    :match="match"
  />
</template>

<style scoped>
.match-row {
  display: grid;
  grid-template-columns:
    [date] 20ch
    [mode] 7ch
    [download] 15ch
    [marker_count] 7ch
    [map] 20ch
    [players] minmax(0, 3fr);

  align-items: center;
  gap: 0.75rem;
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid #e0e0e0;
  font-size: 0.85rem;
}

.match-row .cell {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
