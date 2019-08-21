const app = require('./app.js');

module.exports = {

    convertKey(band = undefined, post = undefined) {
        const returnKeys = {
            bandKey: undefined,
            postKey: undefined,
        };

        if(typeof band === 'string')
            returnKeys.bandKey = band;
        else if(typeof band === 'number') 
            returnKeys.bandKey = band = app.bands[band].band_key;
        
        if(typeof post === 'string')
            returnKeys.postKey = post;
        else if(typeof post === 'number') 
            returnKeys.postKey = app.posts[band].items[post].post_key;
        
        return returnKeys;
    }
};