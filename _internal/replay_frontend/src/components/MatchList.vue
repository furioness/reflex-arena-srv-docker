<script lang="ts" setup>
import MatchDigest from '@/components/MatchDigest.vue'
import {computed, type ComputedRef} from 'vue'
import type {Matches} from "@/types/db-json";

const props = defineProps<{ matches: Matches }>()

const reversedMatches: ComputedRef<Matches> = computed(() =>
  Object.fromEntries(Object.entries(props.matches).reverse()),
)
</script>

<template>
  <!--  header-->
  <div class="match-row">
    <div class="cell date">Date</div>
    <div class="cell mode">Mode</div>
    <div class="cell download">Download</div>
    <div class="cell map">Map</div>
    <div class="cell players">Players</div>
  </div>
  <MatchDigest
    v-for="(replay, filename) in reversedMatches"
    :key="filename"
    :filename="filename"
    :match="replay"
  />
</template>

<style scoped>
.match-row {
  display: grid;
  grid-template-columns:
    [date] 20ch
    [mode] 7ch
    [download] 15ch
    [map] minmax(12ch, 1fr)
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
