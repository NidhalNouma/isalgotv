const CopyWebpackPlugin = require("copy-webpack-plugin");
const path = require("path");

module.exports = {
  plugins: [
    new CopyWebpackPlugin({
      patterns: [
        {
          from: path.resolve(__dirname, "build/static/js/main.*.js"),
          to: path.resolve(__dirname, "../static/js/aichatReact.js"),
          transformPath(targetPath) {
            return "aichatReact.js";
          },
        },
      ],
    }),
  ],
};
