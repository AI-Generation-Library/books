import type { QuartzConfig } from "./quartz/cfg"
import type { QuartzComponent } from "./quartz/components/types"
import type { QuartzEmitterPlugin } from "./quartz/plugins/types"
// Quartz's inline-script-loader transpiles this browser script into a string.
// @ts-ignore
import script from "./book-features.inline"

// Resource-only component: the client attaches controls to the chapter article.
// Registering it through getQuartzComponents keeps it before Quartz's SPA router,
// which dispatches the initial nav event after all component scripts are loaded.
const BookFeaturesResources: QuartzComponent = () => null
BookFeaturesResources.afterDOMLoaded = script

const BookFeatures: QuartzEmitterPlugin = () => ({
  name: "BookFeatures",
  getQuartzComponents: () => [BookFeaturesResources],
  async *emit() {},
  async *partialEmit() {},
})

export function addBookFeatures(config: QuartzConfig): void {
  if (!config.plugins.emitters.some((emitter) => emitter.name === "BookFeatures")) {
    config.plugins.emitters.push(BookFeatures())
  }
}
