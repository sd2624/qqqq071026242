#	band-api  
> 설명

[네이버 밴드 OPEN API](https://developers.band.us/develop/guide/api) 를 사용하여 밴드 OPEN API 를 더 간편하게 사용할 수 있도록 만들었습니다. 
(NPM 등록 X)

<blockquote>사용</blockquote>

<code>npm install band-api</code> 으로 인스톨 후 <code>require('band-api')</code>으로 band-api를 불러옵니다.
	
<blockquote>1. 서비스 정보 설정하기</blockquote> 
제일 먼저, <code>require('band-api').app.config</code> 에서 <code><b>access-token</b></code>, <code><b>client_id</b></code>, <code><b>redirect-uri</b></code> 를 설정합니다.<br>
<h5>예시</h5>
<pre><code>
require('band-api').app.config.access_token = 'access_token'; // 필수 등록
require('band-api').app.config.client_id = 'client_id'; // 필수 등록 X
require('band-api').app.config.redirect_uri = 'redirect_uri'; // 필수 등록 X
</code></pre>
<blockquote>2. 밴드 목록 불러오기</blockquote>
그리고 서비스에 동작할 밴드들을 목록을 불러오기 위해 <br>
<code>require('band-api').init(callbackFunc)</code>를 호출해줍니다. 이때, <code><b>callbackFunc</b></code>는 밴드 목록이 불러오고 나서 호출되는 콜백함수 입니다. <code><b>callbackFunc</b></code> 의 파라미터는 <code><b>err</b></code> 입니다. 타입은 Error 입니다.

밴드 목록이 성공적으로 불러와지면 <code>require('band-api').app.bands</code> 로 확인할 수 있습니다.
참고로, <code>require('band-api').app.bands</code>는 배열 형태로 저장됩니다.

<blockquote>3. 게시글 목록 불러오기</blockquote>
밴드 목록을 받아오시면 그 다음으로 서비스에 동작될 밴드들의 게시글 목록을 불러올 수 있습니다.<br>
이때 <code>require('band-api').posts(callbackFunc, _locale = 'ko-KR')</code> 로 최신 게시글 목록을 불러오며<br>
<code><b>callbackFunc</b></code> 파라미터는 밴드들의 게시글들을 불러오고 나서 호출되는 콜백함수 입니다.<br>
이 함수의 파타미터로는 <code><b>err</b></code>, <code><b>name</b></code>, <code><b>key</b></code> 가 있으며 <code><b>name</b></code> 은 밴드의 이름, <code><b>key</b></code>는 밴드의 키값 입니다.

만약 특정 밴드의 다음 게시글 목록을 불러오고 싶다면 
<code>require('band-api').nextPosts(callbackFunc, _bandIdxOrbandKey, _locale  =  'ko-KR')</code> 로 특정 밴드의 다음 게시글 목록을 불러올 수 있습니다.
마찬가지로 <code><b>callbackFunc</b></code> 파라미터는 밴드들의 게시글들을 불러오고 나서 호출되는 콜백함수 이며, 해당 콜백함수의 파타미터로는 <code><b>err</b></code>, <code><b>key</b></code>, <code><b>item</b></code> 이 있으며 <code><b>key</b></code> 은 밴드의 키값, <code><b>item</b></code>은
불러와진 게시글들이 담겨져 있습니다.

<code><b>_bandIdxOrbandKey</b></code> 파라미터는 밴드 키값 또는  <code>require('band-api').app.bands</code> 배열의 인덱스를 넣으시면 됩니다. 만약, 서비스 할 밴드가 1개 뿐이라면 해당 파라미터 자리에 <code>0</code> 을 넣으시면 됩니다.

밴드들의 게시글들이 불러와지면 <code>require('band-api').app.posts</code> 로 정보를 확인할 수 있습니다.
<code>require('band-api').app.posts</code> 는 <code>require('band-api').app.bands</code> 와는 다르게 Object 형식으로 저장되며 밴드의 키값을 이용하여 해당 밴드의 게시글 목록의 정보를 볼 수 있습니다.

<blockquote>밴드에서 게시글 작성하기</blockquote>

밴드에서 게시글을 작성하시고 싶다면  
<code>require('band-api').createPost(callbackFunc, _bandIdxOrbandKey, _content, _doPush  =  false)</code> 을 
이용하시면 됩니다. <code><b>callbackFunc</b></code> 의 파라미터로는 <code><b>err</b></code>, <code><b>bandKey</b></code>, <code><b>postKey</b></code> 가 있으며 <code><b>bandKey</b></code> 는 게시글이 작성된 밴드의 키값이며 <code><b>postKey</b></code> 는 작성된 게시글의 키값 입니다.

<code><b>_bandIdxOrbandKey</b></code> 는 위와 마찬가지로 서비스 할 밴드가 1개 뿐이라면 해당 파라미터 자리에 <code>0</code>을 넣으시면 됩니다.
<code><b>_content</b></code> 파라미터는 게시글의 내용을 적으시면 되며, <code><b>_doPush</b></code> 는 게시글  작성 시 푸시알림이 울리도록 할건지 정하는 파라미터이며 기본 값은 false 로 되어있습니다.

<blockquote>특정 게시글 보기</blockquote>

<code>require('band-api').detailPost(callbackFunc, _bandIdxOrbandKey, _postIdxOrpostKey)</code> 를 사용하시면 해당 밴드의 특정 게시글을 가져올 수 있습니다.  <code><b>callbackFunc</b></code> 의 파라미터로는 <code><b>err</b></code>, <code><b>bandKey</b></code>, <code><b>post</b></code> 가 있으며 <code><b>bandKey</b></code> 는 게시글이 작성된 밴드의 키값이며 <code><b>post</b></code> 불러온 게시글의 정보가 담겨져있습니다.

<code><b>_bandIdxOrbandKey</b></code> 는 위와 마찬가지로 서비스 할 밴드가 1개 뿐이라면 해당 파라미터 자리에 <code>0</code>을 넣으시면 됩니다.
<code><b>_postIdxOrpostKey</b></code> 파라미터는 해당 밴드의 특정한 게시글의 키값을 입력하시거나 <br><code>0 에서부터 19 중 하나의 숫자</code>를 입력하시면 <code>require('band-api').app.posts</code>내부에 해당 자리에 있는 게시글의 키값으로 변환됩니다. 

<blockquote>게시글 삭제하기</blockquote>

특정한 게시글을 삭제하고 싶다면 
<code>require('band-api').removePost(callbackFunc, _bandIdxOrbandKey, _postIdxOrpostKey)</code> 를 
사용하면 됩니다.  <code><b>callbackFunc</b></code> 의 파라미터로는 <code><b>err</b></code> 가 있습니다.

<code><b>_bandIdxOrbandKey</b></code> 는 위와 마찬가지로 서비스 할 밴드가 1개 뿐이라면 해당 파라미터 자리에 <code>0</code>을 넣으시면 됩니다.
<code><b>_postIdxOrpostKey</b></code> 파라미터는 해당 밴드의 특정한 게시글의 키값을 입력하시거나 <br><code>0 에서부터 19 중 하나의 숫자</code>를 입력하시면 <code>require('band-api').app.posts</code>내부에 해당 자리에 있는 게시글의 키값으로 변환됩니다. 
> 현재까지 구현한 기능들

 - 밴드 목록 불러오기
 - 밴드 게시글 불러오기
 - 밴드의 다음 게시글 불러오기
 - 게시글 삭제
 - 게시글 보기
 - 게시글 쓰기

> 앞으로 구현할 기능들