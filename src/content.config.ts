import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
	// Load Markdown and MDX files in the `src/content/blog/` directory.
	loader: glob({ base: './src/content/blog', pattern: '**/*.{md,mdx}' }),
	// Type-check frontmatter using a schema
	schema: ({ image }) =>
		z.object({
			title: z.string(),
			titleEn: z.string().optional(),
			description: z.string(),
			slug: z.string().optional(),
			// Content categorization system
			// Content categorization system
			category: z.string().optional(),
			audience: z.enum(['children', 'general', 'adult']).optional(),
			tags: z.array(z.string()).optional(),
			ageRange: z.string().optional(),
			moral: z.string().optional(),
			readingTime: z.number().optional(),
			genre: z.string().optional(),
			// Transform string to Date object
			pubDate: z.coerce.date(),
			updatedDate: z.coerce.date().optional(),
			heroImage: image().optional(),
		}),
});

export const collections = { blog };

