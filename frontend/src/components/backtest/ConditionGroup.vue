<template>
  <div class="condition-group" :class="{ 'is-nested': isNested }">
    <div class="group-header">
      <el-radio-group
        :model-value="group.operator"
        @update:model-value="updateOperator"
        size="small"
      >
        <el-radio-button value="AND">AND</el-radio-button>
        <el-radio-button value="OR">OR</el-radio-button>
      </el-radio-group>
      <div class="group-actions">
        <el-button size="small" @click="addRule">
          添加条件
        </el-button>
        <el-button size="small" @click="addSubgroup">
          添加子组
        </el-button>
      </div>
    </div>

    <div class="group-children">
      <div
        v-for="(child, idx) in group.children"
        :key="idx"
        class="child-wrapper"
      >
        <ConditionRule
          v-if="child.type === 'rule'"
          :rule="child"
          @update:rule="updateChild(idx, $event)"
          @remove="removeChild(idx)"
        />
        <ConditionGroup
          v-else-if="child.type === 'group'"
          :group="child"
          :is-nested="true"
          @update:group="updateChild(idx, $event)"
          @remove="removeChild(idx)"
        />
      </div>

      <div v-if="group.children.length === 0" class="empty-hint">
        点击上方按钮添加条件
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import ConditionRule from './ConditionRule.vue'

export default {
  name: 'ConditionGroup',
  components: { ConditionRule },
  props: {
    group: {
      type: Object,
      required: true
    },
    isNested: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:group', 'remove'],
  setup(props, { emit }) {
    function updateOperator(val) {
      emit('update:group', { ...props.group, operator: val })
    }

    function updateChild(idx, updatedChild) {
      const newChildren = [...props.group.children]
      newChildren[idx] = updatedChild
      emit('update:group', { ...props.group, children: newChildren })
    }

    function removeChild(idx) {
      const newChildren = [...props.group.children]
      newChildren.splice(idx, 1)
      emit('update:group', { ...props.group, children: newChildren })
    }

    function addRule() {
      const newChildren = [...props.group.children]
      newChildren.push({
        type: 'rule',
        indicator: 'CLOSE',
        operator: '>',
        threshold: 0
      })
      emit('update:group', { ...props.group, children: newChildren })
    }

    function addSubgroup() {
      const newChildren = [...props.group.children]
      newChildren.push({
        type: 'group',
        operator: 'AND',
        children: []
      })
      emit('update:group', { ...props.group, children: newChildren })
    }

    return {
      updateOperator,
      updateChild,
      removeChild,
      addRule,
      addSubgroup
    }
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables' as *;

.condition-group {
  background-color: $bg-secondary;
  border: 1px solid $border-color;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.condition-group.is-nested {
  margin-left: 20px;
  border-left: 2px solid $accent-blue;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.group-actions {
  display: flex;
  gap: 6px;
}

.group-children {
  padding-left: 4px;
}

.child-wrapper {
  position: relative;
}

.empty-hint {
  color: $text-secondary;
  font-size: 13px;
  padding: 12px 0;
  text-align: center;
}
</style>
