import { getCollection } from 'astro:content';
import { SITE_URL } from '../consts';

export async function GET(context) {
    const posts = (await getCollection('blog')).sort(
        (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
    );

    const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
${posts
            .map((post) => {
                if (!post.data.heroImage) return '';
                const postUrl = `${SITE_URL}/blog/${post.slug || post.id}/`;
                const imageUrl = new URL(post.data.heroImage, SITE_URL).toString();
                return `  <url>
    <loc>${postUrl}</loc>
    <image:image>
      <image:loc>${imageUrl}</image:loc>
      <image:title>${post.data.title}</image:title>
    </image:image>
  </url>`;
            })
            .join('\n')}
</urlset>`;

    return new Response(sitemap, {
        headers: {
            'Content-Type': 'application/xml',
        },
    });
}
