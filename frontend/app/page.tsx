import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background text-foreground p-8">
      <section className="max-w-3xl mx-auto space-y-4">
        <h1 className="text-3xl font-semibold">RBSoftware Frontend Foundation</h1>
        <p className="text-muted-foreground">
          Next.js + TypeScript + Tailwind + shadcn/ui scaffold ready.
        </p>
        <Button>Foundation Ready</Button>
      </section>
    </main>
  );
}
