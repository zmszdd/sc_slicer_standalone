; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9c5d7818_bundle_handleops_reverted () Bool)
(declare-fun c9c5d7818_high_s_counterpart_derivable () Bool)
(declare-fun c9c5d7818_high_s_triggers_invalid_signature_s () Bool)
(declare-fun c9c5d7818_valid_owner_signature_exists () Bool)
(assert
 (= c9c5d7818_bundle_handleops_reverted c9c5d7818_bundle_handleops_reverted))
(assert
 (= c9c5d7818_high_s_counterpart_derivable c9c5d7818_high_s_counterpart_derivable))
(assert
 (= c9c5d7818_high_s_triggers_invalid_signature_s c9c5d7818_high_s_triggers_invalid_signature_s))
(assert
 (= c9c5d7818_valid_owner_signature_exists c9c5d7818_valid_owner_signature_exists))
(define-fun report_preconditions () Bool (and c9c5d7818_valid_owner_signature_exists
     c9c5d7818_high_s_counterpart_derivable
     c9c5d7818_high_s_triggers_invalid_signature_s))
(define-fun report_safety () Bool (=> (and c9c5d7818_valid_owner_signature_exists
         c9c5d7818_high_s_counterpart_derivable
         c9c5d7818_high_s_triggers_invalid_signature_s)
    (not c9c5d7818_bundle_handleops_reverted)))
(define-fun report_effects () Bool (and c9c5d7818_valid_owner_signature_exists
     c9c5d7818_high_s_counterpart_derivable
     c9c5d7818_high_s_triggers_invalid_signature_s
     (not (not c9c5d7818_bundle_handleops_reverted))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
