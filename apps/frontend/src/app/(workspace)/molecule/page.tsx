import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const fetchCache = "force-no-store";

type MoleculePageProps = {
  searchParams?: Promise<{
    provider?: string | string[];
    id?: string | string[];
    q?: string | string[];
  }>;
};

function getSingleValue(input: string | string[] | undefined): string {
  const value = Array.isArray(input) ? input[0] : input;
  return (value ?? "").trim();
}

export default async function MoleculePage({ searchParams }: MoleculePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const provider = getSingleValue(resolvedSearchParams.provider);
  const externalId = getSingleValue(resolvedSearchParams.id);
  const query = getSingleValue(resolvedSearchParams.q);

  const params = new URLSearchParams({
    entity_type: "molecule",
  });
  if (provider) {
    params.set("provider", provider);
  }
  if (externalId) {
    params.set("id", externalId);
  }
  if (query) {
    params.set("q", query);
  }

  redirect(`/workspace?${params.toString()}`);
}
