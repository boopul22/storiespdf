import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { SITE_TITLE, SITE_DESCRIPTION } from '../../consts';
import { categories } from '../../consts/categories';

export async function getStaticPaths() {
    return categories.map(({ slug, title }) => ({
        params: { category: slug },
        props: { categoryName: title },
    }));
}

export async function GET(context) {
    const { category } = context.params;
    const { categoryName } = context.props;

    const allPosts = await getCollection('blog');
    const categoryPosts = allPosts
        .filter((post) => post.data.category === category)
        .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());

    return rss({
        title: `${categoryName} Stories | ${SITE_TITLE}`,
        description: `Latest ${categoryName} stories from ${SITE_TITLE}. ${SITE_DESCRIPTION}`,
        site: context.site,
        items: categoryPosts.map((post) => ({
            ...post.data,
            link: `/blog/${post.slug || post.id}/`,
            pubDate: post.data.pubDate,
            // standard RSS enclosure for images
            enclosure: post.data.heroImage ? {
                url: new URL(post.data.heroImage, context.site).toString(),
                length: 0, // optional, but standard says length required. 0 if unknown is often accepted or estimation needed.
                type: 'image/jpeg' // or check extension
            } : undefined,
            content: post.body, // Optional: full content if desired, or description
        })),
        customData: `<language>en-us</language>`,
    });
}
