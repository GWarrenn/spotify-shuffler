const webpack = require('webpack');

module.exports = {
    // other Webpack config...
    plugins: [
        new webpack.DefinePlugin({
            'process.env.SPOTIPY_CLIENT_ID': JSON.stringify(process.env.SPOTIPY_CLIENT_ID),
        }),
    ],
};