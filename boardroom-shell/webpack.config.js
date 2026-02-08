const path = require('path')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const webpack = require('webpack')

module.exports = {
  entry: './src/index.jsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
    clean: true
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-react']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/index.html',
      filename: 'index.html'
    }),
    new webpack.DefinePlugin({
      'process.env.TRUTH_ENGINE_URL': JSON.stringify(process.env.TRUTH_ENGINE_URL || 'http://localhost:5050'),
      'process.env.OLLAMA_HOST': JSON.stringify(process.env.OLLAMA_HOST || 'http://localhost:11434'),
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
    })
  ],
  devServer: {
    port: process.env.BOARDROOM_PORT || 3000,
    hot: true,
    static: {
      directory: path.join(__dirname, 'dist')
    }
  },
  resolve: {
    extensions: ['.js', '.jsx']
  },
  target: 'electron-renderer'
}