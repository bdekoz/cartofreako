export type ArtifactLifecycle = 'standard' | 'optional' | 'exploration-only';
export type ArtifactPurpose = 'preview' | 'flat-screen' | 'interactive-flat' |
  'print-review' | 'archive-reference' | 'research-comparison';
export type ArtifactFormat = 'png' | 'webp' | 'svg' | 'pdf' | 'full-png';
export type ArtifactPreferenceField = 'projection' | 'format' |
  'authority-class' | 'lifecycle' | 'bytes';
export type ArtifactFallbackField = 'projectionIds' | 'formats' | 'maxBytes' |
  'viewport' | 'authorityClasses';
export interface ArtifactPreference {
  field: ArtifactPreferenceField;
  order?: string[];
  direction?: 'ascending' | 'descending';
}
export interface ArtifactRequestV1 {
  schemaVersion: 'cartofreako-artifact-request-v1';
  requestId: string;
  purpose: ArtifactPurpose;
  passIds?: string[];
  allowedLifecycles?: ArtifactLifecycle[];
  optionalOptIn?: boolean;
  explorationOptIn?: boolean;
  years?: number[];
  sourcePeriods?: string[];
  projectionIds?: string[];
  sliceIds?: string[];
  formats?: ArtifactFormat[];
  viewport?: {width: number; height: number};
  fit?: 'contain';
  transparency?: 'any' | 'required' | 'opaque';
  losslessRequired?: boolean;
  maxBytes?: number;
  interaction?: 'none' | 'projected-picking' | 'geographic-picking';
  authorityClasses?: string[];
  licenses?: string[];
  governance?: string[];
  requireChecksums?: boolean;
  expectedCatalogSha256?: string;
  networkPolicy?: 'offline' | 'catalog-declared-only';
  preferences?: ArtifactPreference[];
  fallbackSequence?: ArtifactFallbackField[];
  humanReviewRequired?: boolean;
}
export interface NormalizedArtifactRequestV1 extends
  Omit<Required<ArtifactRequestV1>, 'viewport' | 'maxBytes' |
    'expectedCatalogSha256' | 'preferences'> {
  viewport: {width: number; height: number} | null;
  maxBytes: number | null;
  expectedCatalogSha256: string | null;
  preferences: Array<Required<ArtifactPreference>>;
}
export interface ArtifactDecisionReceiptV1 {
  schemaVersion: 'cartofreako-artifact-decision-receipt-v1';
  decisionCore: Record<string, unknown>;
  decisionCoreSha256: string;
  runEnvelope: {createdAt: string};
}
export const ArtifactRejectionReason: Readonly<Record<string, string>>;
export function canonicalJson(value: unknown): string;
export function sha256Hex(value: string | Uint8Array): Promise<string>;
export function normalizeArtifactRequest(request: ArtifactRequestV1): NormalizedArtifactRequestV1;
export function selectArtifact(request: ArtifactRequestV1, catalog: unknown,
  options?: {catalogBytes?: Uint8Array; createdAt?: string}): Promise<ArtifactDecisionReceiptV1>;
export function overrideArtifactDecision(prior: ArtifactDecisionReceiptV1,
  replacement: unknown, options: {reason: string; actorLabel: string; createdAt?: string}): Promise<ArtifactDecisionReceiptV1>;
