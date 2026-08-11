const policyVersion = 1;
const runtimeVersion = 'cartofreako-catalog-js-v1';
const nonAuthorityStatement = 'This receipt selects an existing catalog artifact only. It grants no external access, license acceptance, publication, release, research interpretation, archival deposit, or training-data authority.';

export const ArtifactRejectionReason = Object.freeze({
    SUBJECT_MISMATCH: 'SUBJECT_MISMATCH',
    YEAR_MISMATCH: 'YEAR_MISMATCH',
    SOURCE_PERIOD_MISMATCH: 'SOURCE_PERIOD_MISMATCH',
    LIFECYCLE_DISALLOWED: 'LIFECYCLE_DISALLOWED',
    PROJECTION_DISALLOWED: 'PROJECTION_DISALLOWED',
    SLICE_MISMATCH: 'SLICE_MISMATCH',
    FORMAT_UNAVAILABLE: 'FORMAT_UNAVAILABLE',
    VIEWPORT_INCOMPATIBLE: 'VIEWPORT_INCOMPATIBLE',
    INTERACTION_UNSUPPORTED: 'INTERACTION_UNSUPPORTED',
    AUTHORITY_CLASS_DISALLOWED: 'AUTHORITY_CLASS_DISALLOWED',
    MAX_BYTES_EXCEEDED: 'MAX_BYTES_EXCEEDED',
    CHECKSUM_UNAVAILABLE: 'CHECKSUM_UNAVAILABLE',
    METADATA_UNAVAILABLE: 'METADATA_UNAVAILABLE',
    LICENSE_DISALLOWED: 'LICENSE_DISALLOWED',
    TRANSPARENCY_MISMATCH: 'TRANSPARENCY_MISMATCH',
    GOVERNANCE_REVIEW_REQUIRED: 'GOVERNANCE_REVIEW_REQUIRED',
    LOWER_PREFERENCE_RANK: 'LOWER_PREFERENCE_RANK',
    STABLE_TIE_BREAK: 'STABLE_TIE_BREAK'
});

function requireCondition(condition, message) {
    if (!condition) throw new TypeError(message);
}

function uniqueStrings(value, name) {
    requireCondition(Array.isArray(value) && value.every(item =>
        typeof item === 'string' && item.length > 0), `${name} must be strings`);
    requireCondition(new Set(value).size === value.length, `${name} has duplicates`);
    return [...value];
}

export function canonicalJson(value) {
    if (value === null || typeof value === 'boolean' || typeof value === 'string') {
        return JSON.stringify(value);
    }
    if (typeof value === 'number') {
        requireCondition(Number.isFinite(value), 'canonical JSON rejects non-finite numbers');
        return JSON.stringify(Object.is(value, -0) ? 0 : value);
    }
    if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
    requireCondition(value && typeof value === 'object', 'unsupported canonical JSON value');
    return `{${Object.keys(value).sort().map(key =>
        `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
}

export async function sha256Hex(value) {
    const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : value;
    requireCondition(bytes instanceof Uint8Array, 'SHA-256 input must be text or bytes');
    const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

export function normalizeArtifactRequest(request) {
    requireCondition(request?.schemaVersion === 'cartofreako-artifact-request-v1',
        'unsupported artifact request schema');
    requireCondition(typeof request.requestId === 'string' && request.requestId.length > 0,
        'requestId is required');
    const purposes = new Set(['preview', 'flat-screen', 'interactive-flat',
        'print-review', 'archive-reference', 'research-comparison']);
    requireCondition(purposes.has(request.purpose), 'invalid purpose');
    const result = {
        schemaVersion: request.schemaVersion,
        requestId: request.requestId,
        purpose: request.purpose,
        passIds: uniqueStrings(request.passIds ?? [], 'passIds'),
        allowedLifecycles: uniqueStrings(request.allowedLifecycles ?? ['standard'],
            'allowedLifecycles'),
        optionalOptIn: request.optionalOptIn ?? false,
        explorationOptIn: request.explorationOptIn ?? false,
        years: [...(request.years ?? [])],
        sourcePeriods: uniqueStrings(request.sourcePeriods ?? [], 'sourcePeriods'),
        projectionIds: uniqueStrings(request.projectionIds ?? [], 'projectionIds'),
        sliceIds: uniqueStrings(request.sliceIds ?? [], 'sliceIds'),
        formats: uniqueStrings(request.formats ?? ['png', 'webp'], 'formats'),
        viewport: request.viewport ?? null,
        fit: request.fit ?? 'contain',
        transparency: request.transparency ?? 'any',
        losslessRequired: request.losslessRequired ?? false,
        maxBytes: request.maxBytes ?? null,
        interaction: request.interaction ?? 'none',
        authorityClasses: uniqueStrings(request.authorityClasses ?? [], 'authorityClasses'),
        licenses: uniqueStrings(request.licenses ?? [], 'licenses'),
        governance: uniqueStrings(request.governance ?? [], 'governance'),
        requireChecksums: request.requireChecksums ?? true,
        expectedCatalogSha256: request.expectedCatalogSha256 ?? null,
        networkPolicy: request.networkPolicy ?? 'offline',
        preferences: (request.preferences ?? []).map(value => ({
            field: value.field,
            order: [...(value.order ?? [])],
            direction: value.direction ?? 'ascending'
        })),
        fallbackSequence: uniqueStrings(request.fallbackSequence ?? [], 'fallbackSequence'),
        humanReviewRequired: request.humanReviewRequired ?? false
    };
    requireCondition(result.allowedLifecycles.every(value =>
        ['standard', 'optional', 'exploration-only'].includes(value)),
    'invalid lifecycle');
    requireCondition(!result.allowedLifecycles.includes('optional') || result.optionalOptIn,
        'optional lifecycle requires optionalOptIn');
    requireCondition(!result.allowedLifecycles.includes('exploration-only')
        || (result.explorationOptIn && result.humanReviewRequired),
    'exploration-only requires explorationOptIn and humanReviewRequired');
    requireCondition(result.formats.every(value =>
        ['png', 'webp', 'svg', 'pdf', 'full-png'].includes(value)), 'invalid format');
    requireCondition(['offline', 'catalog-declared-only'].includes(result.networkPolicy),
        'invalid network policy');
    requireCondition(result.fit === 'contain', 'only contain fit is supported');
    return result;
}

function artifactVariants(artifact) {
    const candidates = [
        ['png', 'screen-png', artifact.screen?.png, artifact.screen],
        ['webp', 'screen-webp', artifact.screen?.webp, artifact.screen],
        ['svg', 'parent-svg', artifact.parents?.svg, null],
        ['pdf', 'parent-pdf', artifact.parents?.pdf, null],
        ['full-png', 'parent-full-png', artifact.parents?.fullPng, null]
    ];
    return candidates.filter(([, , file]) => file).map(([format, id, file, screen]) => ({
        artifact,
        format,
        variantId: id,
        file,
        screen
    }));
}

function rejectionReasons(candidate, request) {
    const {artifact, format, file, screen} = candidate;
    const reasons = [];
    if (request.passIds.length && !request.passIds.includes(artifact.pass.id))
        reasons.push(ArtifactRejectionReason.SUBJECT_MISMATCH);
    if (request.years.length && (!Number.isInteger(artifact.pass.year)
        || !request.years.includes(artifact.pass.year)))
        reasons.push(ArtifactRejectionReason.YEAR_MISMATCH);
    const sourcePeriod = artifact.pass.sourcePeriod
        ?? artifact.evidence?.sourcePeriod ?? 'UNAVAILABLE';
    if (request.sourcePeriods.length) {
        if (sourcePeriod === 'UNAVAILABLE')
            reasons.push(ArtifactRejectionReason.METADATA_UNAVAILABLE);
        else if (!request.sourcePeriods.includes(sourcePeriod))
            reasons.push(ArtifactRejectionReason.SOURCE_PERIOD_MISMATCH);
    }
    if (!request.allowedLifecycles.includes(artifact.pass.lifecycle))
        reasons.push(ArtifactRejectionReason.LIFECYCLE_DISALLOWED);
    if (request.projectionIds.length
        && !request.projectionIds.includes(artifact.projection.id))
        reasons.push(ArtifactRejectionReason.PROJECTION_DISALLOWED);
    const sliceId = artifact.slice?.id ?? 'whole-map';
    if (request.sliceIds.length && !request.sliceIds.includes(sliceId))
        reasons.push(ArtifactRejectionReason.SLICE_MISMATCH);
    if (!request.formats.includes(format))
        reasons.push(ArtifactRejectionReason.FORMAT_UNAVAILABLE);
    if (request.viewport && (!screen
        || screen.canvas.width !== request.viewport.width
        || screen.canvas.height !== request.viewport.height))
        reasons.push(ArtifactRejectionReason.VIEWPORT_INCOMPATIBLE);
    if (request.interaction !== 'none' && !screen)
        reasons.push(ArtifactRejectionReason.INTERACTION_UNSUPPORTED);
    if (request.interaction === 'geographic-picking'
        && !['face-qualified', 'candidates'].includes(artifact.projection.inverseMode))
        reasons.push(ArtifactRejectionReason.INTERACTION_UNSUPPORTED);
    if (request.authorityClasses.length
        && !request.authorityClasses.includes(file.authorityClass))
        reasons.push(ArtifactRejectionReason.AUTHORITY_CLASS_DISALLOWED);
    if (request.maxBytes !== null && file.bytes > request.maxBytes)
        reasons.push(ArtifactRejectionReason.MAX_BYTES_EXCEEDED);
    if (request.requireChecksums && !/^[0-9a-f]{64}$/.test(file.sha256 ?? ''))
        reasons.push(ArtifactRejectionReason.CHECKSUM_UNAVAILABLE);
    if (request.losslessRequired && file.lossless !== true
        && !['svg', 'pdf'].includes(format))
        reasons.push(ArtifactRejectionReason.FORMAT_UNAVAILABLE);
    if (request.transparency !== 'any') {
        if (!file.transparency || file.transparency === 'UNAVAILABLE')
            reasons.push(ArtifactRejectionReason.METADATA_UNAVAILABLE);
        else if ((request.transparency === 'required' && file.transparency !== 'alpha')
            || (request.transparency === 'opaque' && file.transparency !== 'opaque'))
            reasons.push(ArtifactRejectionReason.TRANSPARENCY_MISMATCH);
    }
    if (request.licenses.length) {
        const license = artifact.evidence?.licenseSpdx ?? 'UNAVAILABLE';
        if (license === 'UNAVAILABLE')
            reasons.push(ArtifactRejectionReason.METADATA_UNAVAILABLE);
        else if (!request.licenses.includes(license))
            reasons.push(ArtifactRejectionReason.LICENSE_DISALLOWED);
    }
    if (request.governance.length) {
        const governance = artifact.evidence?.governance ?? 'UNAVAILABLE';
        if (governance === 'UNAVAILABLE')
            reasons.push(ArtifactRejectionReason.METADATA_UNAVAILABLE);
        else if (!request.governance.includes(governance))
            reasons.push(ArtifactRejectionReason.GOVERNANCE_REVIEW_REQUIRED);
    }
    return [...new Set(reasons)].sort();
}

function rank(candidate, preferences) {
    return preferences.map(preference => {
        let value;
        switch (preference.field) {
        case 'projection': value = candidate.artifact.projection.id; break;
        case 'format': value = candidate.format; break;
        case 'authority-class': value = candidate.file.authorityClass; break;
        case 'lifecycle': value = candidate.artifact.pass.lifecycle; break;
        case 'bytes': return preference.direction === 'descending'
            ? -candidate.file.bytes : candidate.file.bytes;
        default: throw new TypeError(`unknown preference field ${preference.field}`);
        }
        const index = preference.order.indexOf(value);
        return index < 0 ? preference.order.length : index;
    });
}

function compareRank(left, right) {
    for (let index = 0; index < Math.max(left.rankVector.length,
        right.rankVector.length); ++index) {
        const difference = (left.rankVector[index] ?? 0) - (right.rankVector[index] ?? 0);
        if (difference) return difference;
    }
    return `${left.artifactId}\u0000${left.variantId}`.localeCompare(
        `${right.artifactId}\u0000${right.variantId}`, 'en');
}

function candidateReceipt(candidate, reasons) {
    return {
        artifactId: candidate.artifact.id,
        variantId: candidate.variantId,
        rankVector: candidate.rankVector,
        rejectionReasonCodes: reasons
    };
}

function selectionRecord(candidate) {
    if (!candidate) return null;
    const artifact = candidate.artifact;
    return {
        artifactId: artifact.id,
        variantId: candidate.variantId,
        file: candidate.file,
        authorityClass: candidate.file.authorityClass,
        lifecycle: artifact.pass.lifecycle,
        projectionId: artifact.projection.id,
        layoutId: artifact.projection.layoutId ?? artifact.projection.id,
        sliceId: artifact.slice?.id ?? 'whole-map',
        sourcePeriod: artifact.pass.sourcePeriod
            ?? artifact.evidence?.sourcePeriod ?? 'UNAVAILABLE',
        limitations: [...artifact.limitations],
        interaction: candidate.screen ? {
            projectedPicking: true,
            geographicPicking: ['face-qualified', 'candidates']
                .includes(artifact.projection.inverseMode),
            projectedToScreen: candidate.screen.projectedToScreen,
            screenToProjected: candidate.screen.screenToProjected
        } : null
    };
}

const fallbackValues = Object.freeze({
    projectionIds: [],
    formats: ['png', 'webp', 'svg', 'pdf', 'full-png'],
    maxBytes: null,
    viewport: null,
    authorityClasses: []
});

function applyFallback(request, field) {
    requireCondition(Object.hasOwn(fallbackValues, field),
        `unsupported fallback field ${field}`);
    const before = request[field];
    const after = Array.isArray(fallbackValues[field])
        ? [...fallbackValues[field]] : fallbackValues[field];
    return {
        request: {...request, [field]: after},
        relaxation: {
            field,
            before,
            after,
            reason: 'Explicit request fallback applied after no candidate satisfied all prior constraints.'
        }
    };
}

function evaluateCandidates(candidates, request) {
    const evaluated = candidates.map(candidate => ({candidate,
        reasons: rejectionReasons(candidate, request)}));
    const survivors = evaluated.filter(value => value.reasons.length === 0)
        .map(value => value.candidate).sort(compareRank);
    return {evaluated, survivors};
}

export async function selectArtifact(request, catalog, options = {}) {
    const normalizedRequest = normalizeArtifactRequest(request);
    requireCondition(catalog?.schema === 'cartofreako-artifacts-v1'
        && catalog.catalogVersion === 1 && Array.isArray(catalog.artifacts),
    'unsupported artifact catalog');
    const requestCanonical = canonicalJson(normalizedRequest);
    const catalogCanonical = canonicalJson(catalog);
    const requestSha256 = await sha256Hex(requestCanonical);
    const catalogSha256 = await sha256Hex(options.catalogBytes
        ?? new TextEncoder().encode(catalogCanonical));
    requireCondition(normalizedRequest.expectedCatalogSha256 === null
        || normalizedRequest.expectedCatalogSha256 === catalogSha256,
    'catalog hash does not match expectedCatalogSha256');
    const candidates = catalog.artifacts.flatMap(artifact => artifactVariants(artifact))
        .map(candidate => ({...candidate,
            rankVector: rank(candidate, normalizedRequest.preferences)}));
    let effectiveRequest = normalizedRequest;
    let {evaluated, survivors} = evaluateCandidates(candidates, effectiveRequest);
    const relaxations = [];
    for (const field of normalizedRequest.fallbackSequence) {
        if (survivors.length) break;
        const fallback = applyFallback(effectiveRequest, field);
        effectiveRequest = fallback.request;
        relaxations.push(fallback.relaxation);
        ({evaluated, survivors} = evaluateCandidates(candidates, effectiveRequest));
    }
    const selected = survivors[0] ?? null;
    const evaluatedCandidates = evaluated.map(({candidate, reasons}) => {
        const finalReasons = [...reasons];
        if (!reasons.length && selected && candidate !== selected) {
            finalReasons.push(compareRank(candidate, selected) === 0
                ? ArtifactRejectionReason.STABLE_TIE_BREAK
                : ArtifactRejectionReason.LOWER_PREFERENCE_RANK);
        }
        return candidateReceipt(candidate, finalReasons);
    }).sort((left, right) => `${left.artifactId}\u0000${left.variantId}`
        .localeCompare(`${right.artifactId}\u0000${right.variantId}`, 'en'));
    const requiresReview = selected && (normalizedRequest.humanReviewRequired
        || selected.artifact.pass.lifecycle === 'exploration-only');
    const decisionCore = {
        requestId: normalizedRequest.requestId,
        requestSha256,
        normalizedRequest,
        catalog: {
            schema: catalog.schema,
            catalogVersion: catalog.catalogVersion,
            sourceRevision: catalog.sourceRevision,
            sha256: catalogSha256
        },
        selectionPolicyVersion: policyVersion,
        runtimeVersion,
        outcome: selected ? (requiresReview ? 'requires-human-review' : 'selected')
            : 'no-match',
        selection: selectionRecord(selected),
        evaluatedCandidates,
        relaxations,
        nonAuthorityStatement
    };
    return {
        schemaVersion: 'cartofreako-artifact-decision-receipt-v1',
        decisionCore,
        decisionCoreSha256: await sha256Hex(canonicalJson(decisionCore)),
        runEnvelope: {createdAt: options.createdAt ?? new Date().toISOString()}
    };
}

export async function overrideArtifactDecision(priorReceipt, replacement,
    {reason, actorLabel, createdAt} = {}) {
    requireCondition(priorReceipt?.schemaVersion
        === 'cartofreako-artifact-decision-receipt-v1', 'invalid prior receipt');
    requireCondition(typeof reason === 'string' && reason
        && typeof actorLabel === 'string' && actorLabel, 'override needs reason and actorLabel');
    const decisionCore = {
        ...priorReceipt.decisionCore,
        priorReceiptSha256: priorReceipt.decisionCoreSha256,
        outcome: 'requires-human-review',
        selection: replacement,
        override: {
            priorSelection: priorReceipt.decisionCore.selection,
            replacement,
            reason,
            actorLabel
        }
    };
    return {
        schemaVersion: priorReceipt.schemaVersion,
        decisionCore,
        decisionCoreSha256: await sha256Hex(canonicalJson(decisionCore)),
        runEnvelope: {createdAt: createdAt ?? new Date().toISOString()}
    };
}
