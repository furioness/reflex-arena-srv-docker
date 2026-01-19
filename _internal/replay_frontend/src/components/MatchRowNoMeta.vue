<script lang="ts" setup>

import {formatDate} from "@/utils/utils.ts";

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
      <a v-if="match.downloadable" :href="filename">{{ filename }}</a>
      <span v-else class="disabled">filename</span>
    </div>

  </div>
</template>
