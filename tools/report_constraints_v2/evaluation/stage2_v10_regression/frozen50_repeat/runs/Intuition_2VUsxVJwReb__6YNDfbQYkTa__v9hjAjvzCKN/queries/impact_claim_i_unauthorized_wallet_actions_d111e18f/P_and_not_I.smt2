; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf910bd2_hash_excludes_signature () Bool)
(declare-fun cbf910bd2_signature_length_bytes () Int)
(declare-fun cbf910bd2_time_window_suffix_bytes () Int)
(declare-fun cbf910bd2_unauthorized_wallet_action_executed () Bool)
(declare-fun cbf910bd2_window_authenticated_by_owner () Bool)
(assert
 (= cbf910bd2_hash_excludes_signature cbf910bd2_hash_excludes_signature))
(assert
 (= cbf910bd2_signature_length_bytes cbf910bd2_signature_length_bytes))
(assert
 (= cbf910bd2_time_window_suffix_bytes cbf910bd2_time_window_suffix_bytes))
(assert
 (= cbf910bd2_unauthorized_wallet_action_executed cbf910bd2_unauthorized_wallet_action_executed))
(assert
 (= cbf910bd2_window_authenticated_by_owner cbf910bd2_window_authenticated_by_owner))
(define-fun report_preconditions () Bool (and (= 77 cbf910bd2_signature_length_bytes)
     (= 12 cbf910bd2_time_window_suffix_bytes)
     cbf910bd2_hash_excludes_signature))
(define-fun report_safety () Bool (=> (and (= 77 cbf910bd2_signature_length_bytes)
         (= 12 cbf910bd2_time_window_suffix_bytes)
         cbf910bd2_hash_excludes_signature)
    (and cbf910bd2_window_authenticated_by_owner
         (not cbf910bd2_unauthorized_wallet_action_executed))))
(define-fun report_effects () Bool (and (= 77 cbf910bd2_signature_length_bytes)
     (= 12 cbf910bd2_time_window_suffix_bytes)
     cbf910bd2_hash_excludes_signature
     (not (and cbf910bd2_window_authenticated_by_owner
               (not cbf910bd2_unauthorized_wallet_action_executed)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
