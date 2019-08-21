const bandAPI = require('band-api');

bandAPI.app.config.access_token = '';
bandAPI.init((err) => {
    if(err)
        throw err;
    
    console.log('성공적으로 밴드 목록을 불러왔습니다!');
});

bandAPI.createPost((err, bandKey, postKey) => {
    if(err)
        throw err;
    
    console.log(`성공적으로 게시글을 올렸습니다. 게시글 키: ${postKey}`);
}, 0, '안녕하세요 ^^');