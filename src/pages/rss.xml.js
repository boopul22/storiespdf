import { getCollection } from 'astro:content';
import rss from '@astrojs/rss';
import { SITE_DESCRIPTION, SITE_TITLE } from '../consts';

export async function GET(context) {
	const posts = (await getCollection('blog')).sort(
		(a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
	);
	return rss({
		title: SITE_TITLE,
		description: SITE_DESCRIPTION,
		site: context.site,
		items: posts.map((post) => ({
			...post.data,
			link: `/blog/${post.id}/`,
			pubDate: post.data.pubDate,
			enclosure: post.data.heroImage ? {
				url: new URL(post.data.heroImage, context.site).toString(),
				length: 0,
				type: 'image/jpeg'
			} : undefined,
		})),
		customData: `<language>en-us</language>`,
	});
}
