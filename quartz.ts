import { loadQuartzConfig, loadQuartzLayout } from "./quartz/plugins/loader/config-loader"
import { addFolderLinks } from "./folder-links"
import { addBookFeatures } from "./book-features"
import { registerCondition } from "./quartz/plugins/loader/conditions"

registerCondition("not-book-home", (props) =>
  props.fileData.slug !== "index" && props.fileData.frontmatter?.bookHome !== true,
)

const config = await loadQuartzConfig()
addFolderLinks(config)
addBookFeatures(config)
export default config
export const layout = await loadQuartzLayout()
