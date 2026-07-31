/**
 * 食材图标映射
 * 来源：docs/Design.md §9.2 + 用户提供的图片
 * 用途：Loading.vue 思考动画 / 落停动效
 *
 * 注意：这是"食材图标"（单个食材 + 白底），不是菜品配图。
 * 菜品配图是另一套资产（高级白盘俯拍），见 PRD §3.2.3.1。
 */
import broccoliUrl from '@/assets/ingredients/broccoli.jpg'
import cabbageUrl from '@/assets/ingredients/cabbage.jpg'
import cornUrl from '@/assets/ingredients/corn.jpg'
import garlicUrl from '@/assets/ingredients/garlic.jpg'
import gingerUrl from '@/assets/ingredients/ginger.jpg'
import grapeUrl from '@/assets/ingredients/grape.jpg'
import pearUrl from '@/assets/ingredients/pear.jpg'
import shrimpUrl from '@/assets/ingredients/shrimp.jpg'
import tomatoUrl from '@/assets/ingredients/tomato.jpg'

export interface Ingredient {
  /** 英文 key，文件名同名 */
  key: string
  /** 中文显示名 */
  name: string
  /** 静态资源路径（Vite 处理后） */
  url: string
}

/** 食材池（MVP：9 种；后续按 PRD §9.2 要求扩到 ≥ 20 种） */
export const INGREDIENTS: Ingredient[] = [
  { key: 'tomato', name: '番茄', url: tomatoUrl },
  { key: 'broccoli', name: '西兰花', url: broccoliUrl },
  { key: 'grape', name: '葡萄', url: grapeUrl },
  { key: 'pear', name: '梨', url: pearUrl },
  { key: 'cabbage', name: '白菜', url: cabbageUrl },
  { key: 'garlic', name: '大蒜', url: garlicUrl },
  { key: 'ginger', name: '姜', url: gingerUrl },
  { key: 'shrimp', name: '虾', url: shrimpUrl },
  { key: 'corn', name: '玉米', url: cornUrl },
]

/** 中文名 → 食材（MVP mock 数据 / 顺手做推荐匹配用） */
export const INGREDIENT_BY_NAME: Record<string, Ingredient> = Object.fromEntries(
  INGREDIENTS.map((i) => [i.name, i]),
)

/** 随机选一个食材 */
export function pickRandomIngredient(): Ingredient {
  return INGREDIENTS[Math.floor(Math.random() * INGREDIENTS.length)]
}