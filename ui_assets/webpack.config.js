// Source: https://digitalhedgehog.org/articles/how-to-use-flask-with-webpack

const path = require('path');
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const RemoveEmptyScriptsPlugin = require('webpack-remove-empty-scripts')

module.exports = {
  entry: {
    main: './src/index.js',
    vonage: './src/nexmoClient.js',
    styles: '/src/styles.css'
  },
  output: {
    filename: '[name].[contenthash].js',
    publicPath: '/static/dist/',
    path: path.resolve(__dirname, '..','ui', 'static', 'dist'),
    clean: true
  },
  module: {
    rules: [{
      test: /\.css$/,
        use: [
          MiniCssExtractPlugin.loader,
            {
              loader: 'css-loader'
            },
            {
              loader: 'sass-loader',
              options: {
                sourceMap: true,
              }
            }
        ]
    }]
  },
  plugins: [
      new WebpackManifestPlugin(),
      new RemoveEmptyScriptsPlugin(),
      new MiniCssExtractPlugin({
            filename: '[name].[contenthash].css'
        })
  ]
};