<script lang="ts" setup>
import MatchRowWithMeta from '@/components/MatchRowWithMeta.vue'
import MatchRowNoMeta from '@/components/MatchRowNoMeta.vue'
import type {Match} from "@/types/db-json";

const {match, filename} = defineProps<{
  match: Match
  filename: string
}>()
</script>
<template>
  <MatchRowWithMeta v-if="match.metadata" :filename="filename" :match="match"/>
  <MatchRowNoMeta v-else :filename="filename" :match="match"/>
</template>
