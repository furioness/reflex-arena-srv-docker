<script lang="ts" setup>
import {formatDate, getReplayUrl} from '@/utils/utils.ts'
import type {Match} from "@/types/db-json";

defineProps<{
  match: Match & { metadata: null }
  filename: string
}>()
</script>

<template>
  <div class="match-row">
    <div class="cell date">
      {{ formatDate(match.finished_at) }}
    </div>

    <div class="cell">
      <a v-if="match.downloadable" :href="getReplayUrl(filename)">{{ filename }}</a>
      <span v-else class="disabled">filename</span>
    </div>
  </div>
</template>
