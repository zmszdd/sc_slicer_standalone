; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9b182c01_hash_covers_suffix () Bool)
(declare-fun c9b182c01_signature_length_bytes () Int)
(declare-fun c9b182c01_time_window_suffix_bytes () Int)
(declare-fun c9b182c01_window_authenticated_by_signature () Bool)
(assert
 (= c9b182c01_hash_covers_suffix c9b182c01_hash_covers_suffix))
(assert
 (= c9b182c01_signature_length_bytes c9b182c01_signature_length_bytes))
(assert
 (= c9b182c01_time_window_suffix_bytes c9b182c01_time_window_suffix_bytes))
(assert
 (= c9b182c01_window_authenticated_by_signature c9b182c01_window_authenticated_by_signature))
(define-fun report_preconditions () Bool (and (= 77 c9b182c01_signature_length_bytes)
     (= 12 c9b182c01_time_window_suffix_bytes)
     (not c9b182c01_hash_covers_suffix)))
(define-fun report_safety () Bool (=> (and (= 77 c9b182c01_signature_length_bytes)
         (= 12 c9b182c01_time_window_suffix_bytes)
         (not c9b182c01_hash_covers_suffix))
    c9b182c01_window_authenticated_by_signature))
(define-fun report_effects () Bool (and (= 77 c9b182c01_signature_length_bytes)
     (= 12 c9b182c01_time_window_suffix_bytes)
     (not c9b182c01_hash_covers_suffix)
     (not c9b182c01_window_authenticated_by_signature)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
